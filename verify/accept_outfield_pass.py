import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ACCEPTANCE_DIR = os.path.join(ROOT, "acceptance")
INBOX_DIR = os.path.join(ACCEPTANCE_DIR, "inbox")
QUARANTINE_DIR = os.path.join(ACCEPTANCE_DIR, "quarantine")
CONSUMED_DIR = os.path.join(QUARANTINE_DIR, "inbox_consumed")
SUMMARY_MATRIX_PATH = os.path.join(ACCEPTANCE_DIR, "summary_matrix.json")
FREEZE_MANIFEST_PATH = os.path.join(ROOT, "freeze_manifest.json")

REJECT_TOKENS = ["TEMPLATE", "REPLACE_ME"]


def die(msg, code=2):
    print("ERROR:", msg)
    sys.exit(code)


def ensure_dirs():
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(CONSUMED_DIR, exist_ok=True)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def decode_text_best_effort(b):
    if b.startswith(b"\xef\xbb\xbf"):
        return b.decode("utf-8-sig")
    if b.startswith(b"\xff\xfe"):
        return b.decode("utf-16le")
    if b.startswith(b"\xfe\xff"):
        return b.decode("utf-16be")

    nul = b.count(b"\x00")
    if len(b) > 0 and (nul / len(b)) > 0.10:
        try:
            return b.decode("utf-16")
        except Exception:
            pass

    return b.decode("utf-8")


def read_text(path):
    return decode_text_best_effort(read_bytes(path))


def load_json(path):
    return json.loads(read_text(path))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True)


def reject_if_tokens_present(raw_text, context):
    for tok in REJECT_TOKENS:
        if tok in raw_text:
            die("reject token found in " + context + ": " + tok)


def sealed_pack_info():
    if os.path.exists(FREEZE_MANIFEST_PATH):
        m = load_json(FREEZE_MANIFEST_PATH)
        vp = m.get("verify_pack") or {}
        zn = vp.get("zip_name")
        hs = vp.get("sha256")
        if zn and hs:
            return {"zip_name": zn, "sha256": hs}

    if os.path.exists(SUMMARY_MATRIX_PATH):
        sm = load_json(SUMMARY_MATRIX_PATH)
        ep = sm.get("external_pack") or {}
        zn = ep.get("zip_name")
        hs = ep.get("sha256")
        if zn and hs:
            return {"zip_name": zn, "sha256": hs}

    die("sealed pack info not found (freeze_manifest.json or acceptance/summary_matrix.json)")


def utc_iso_z_precise():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def coerce_dest_name(name):
    base = os.path.basename(name).strip()
    base = base.replace(".json", "")
    if not base:
        die("dest_name_without_ext is empty")
    for ch in base:
        if not (ch.isalnum() or ch in ("-", "_")):
            die("dest name contains invalid char: " + ch)
    return base


def normalize_outfield_to_v2(obj, filename_hint):
    if not isinstance(obj, dict):
        return None, "not an object"

    if "row_outfield" in obj and isinstance(obj["row_outfield"], dict):
        obj = obj["row_outfield"]

    # v2 already
    if obj.get("kind") == "outfield":
        row = dict(obj)
        if "file" not in row:
            row["file"] = filename_hint
        return row, None

    # v1 legacy nested
    env = obj.get("environment")
    pack = obj.get("pack")
    res = obj.get("result")
    if isinstance(env, dict) and isinstance(pack, dict) and isinstance(res, dict):
        row = {
            "file": filename_hint,
            "kind": "outfield",
            "pack_zip_name": pack.get("zip_name"),
            "pack_sha256": pack.get("sha256"),
            "os": env.get("os"),
            "python": env.get("python"),
            "machine": env.get("machine"),
            "submitted_utc": obj.get("submitted_utc"),
            "overall_status": res.get("overall_status"),
            "started_utc": res.get("started_utc"),
            "run_id": obj.get("run_id"),
        }
        return row, None

    return None, "not outfield kind"


def require_fields(row, fields):
    missing = [k for k in fields if k not in row or row.get(k) in (None, "")]
    if missing:
        return False, missing
    return True, []


def validate_row_outfield_v2(row, sealed):
    ok, missing = require_fields(
        row,
        [
            "kind",
            "file",
            "pack_zip_name",
            "pack_sha256",
            "os",
            "python",
            "machine",
            "submitted_utc",
            "started_utc",
            "run_id",
            "overall_status",
        ],
    )
    if not ok:
        die("missing required fields: " + ", ".join(missing))

    if row.get("kind") != "outfield":
        die("kind must be outfield")

    if row.get("overall_status") != "PASS":
        die("overall_status must be PASS")

    if row.get("pack_zip_name") != sealed["zip_name"]:
        die("pack_zip_name mismatch")

    if str(row.get("pack_sha256", "")).upper() != str(sealed["sha256"]).upper():
        die("pack_sha256 mismatch")

    reject_if_tokens_present(json.dumps(row, ensure_ascii=True), "row_outfield values")


def load_previous_internal_rows():
    if not os.path.exists(SUMMARY_MATRIX_PATH):
        return []
    try:
        prev = load_json(SUMMARY_MATRIX_PATH)
        rows = prev.get("rows_internal")
        if isinstance(rows, list):
            return rows
    except Exception:
        return []
    return []


def try_load_consumed_outfield_v2(path, filename):
    raw = None
    try:
        raw = read_text(path)
        reject_if_tokens_present(raw, "consumed file")
        obj = json.loads(raw)
        row, err = normalize_outfield_to_v2(obj, filename)
        if row is None:
            return None, err
        if row.get("kind") != "outfield":
            return None, "not outfield kind"
        row2 = dict(row)
        row2["file"] = filename
        return row2, None
    except Exception as e:
        if raw is not None:
            return None, "json/normalize failed: " + str(e)
        return None, "read/decode failed: " + str(e)


def build_summary_matrix(verbose=False):
    sealed = sealed_pack_info()

    rows_outfield = []
    errors = []

    if os.path.isdir(CONSUMED_DIR):
        for fn in sorted(os.listdir(CONSUMED_DIR)):
            if not fn.lower().endswith(".json"):
                continue
            p = os.path.join(CONSUMED_DIR, fn)
            row, err = try_load_consumed_outfield_v2(p, fn)
            if row is None:
                errors.append({"file": fn, "error": err})
                continue
            rows_outfield.append(row)

    rows_internal = load_previous_internal_rows()

    external_generated_utc = "UNKNOWN"
    if os.path.exists(SUMMARY_MATRIX_PATH):
        try:
            prev = load_json(SUMMARY_MATRIX_PATH)
            ep = prev.get("external_pack") or {}
            if isinstance(ep, dict) and ep.get("generated_utc"):
                external_generated_utc = ep.get("generated_utc")
        except Exception:
            pass

    matrix = {
        "generated_at_utc": utc_iso_z_precise(),
        "count_internal": len(rows_internal),
        "count_outfield": len(rows_outfield),
        "rows_internal": rows_internal,
        "rows_outfield": rows_outfield,
        "external_pack": {
            "zip_name": sealed["zip_name"],
            "sha256": sealed["sha256"],
            "generated_utc": external_generated_utc,
        },
    }

    write_json(SUMMARY_MATRIX_PATH, matrix)

    if verbose and errors:
        print("WARN: some consumed files were skipped")
        for e in errors:
            print("SKIP:", e.get("file"), "|", e.get("error"))

    return matrix


def accept_one(input_json, dest_name_without_ext):
    ensure_dirs()

    if not os.path.exists(input_json):
        die("input_json not found: " + input_json)

    raw = read_text(input_json)
    reject_if_tokens_present(raw, "input_json")
    obj = json.loads(raw)

    sealed = sealed_pack_info()
    dest_name = coerce_dest_name(dest_name_without_ext)
    dest_filename = dest_name + ".json"
    dest_path = os.path.join(CONSUMED_DIR, dest_filename)

    if os.path.exists(dest_path):
        die("dest already exists: " + dest_path)

    row, err = normalize_outfield_to_v2(obj, dest_filename)
    if row is None:
        die("invalid outfield json: " + str(err))

    row_out = dict(row)
    row_out["file"] = dest_filename
    row_out["kind"] = "outfield"

    validate_row_outfield_v2(row_out, sealed)

    write_json(dest_path, row_out)

    try:
        abs_in = os.path.abspath(input_json)
        abs_inbox = os.path.abspath(INBOX_DIR)
        if os.path.commonpath([abs_in, abs_inbox]) == abs_inbox:
            os.remove(input_json)
    except Exception:
        pass

    matrix = build_summary_matrix(verbose=False)

    print("OK: accepted outfield PASS")
    print("WROTE:", dest_path)
    print("UPDATED:", SUMMARY_MATRIX_PATH)
    print("count_outfield:", matrix.get("count_outfield"))


def normalize_consumed(filename):
    ensure_dirs()

    fn = os.path.basename(filename)
    if not fn.lower().endswith(".json"):
        die("filename must end with .json")

    path = os.path.join(CONSUMED_DIR, fn)
    if not os.path.exists(path):
        die("consumed file not found: " + path)

    raw = read_text(path)
    reject_if_tokens_present(raw, "consumed file")

    obj = json.loads(raw)
    row, err = normalize_outfield_to_v2(obj, fn)
    if row is None:
        die("cannot normalize: " + str(err))

    sealed = sealed_pack_info()
    row_out = dict(row)
    row_out["file"] = fn
    row_out["kind"] = "outfield"

    # NOTE: normalize only if it is a PASS and sealed pack matches
    validate_row_outfield_v2(row_out, sealed)

    backup = path + ".orig.json"
    if os.path.exists(backup):
        die("backup already exists: " + backup)

    os.rename(path, backup)
    write_json(path, row_out)

    build_summary_matrix(verbose=False)

    print("OK: normalized consumed to v2")
    print("BACKUP:", backup)
    print("WROTE:", path)
    print("UPDATED:", SUMMARY_MATRIX_PATH)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--rebuild":
        verbose = ("--verbose" in sys.argv[2:])
        ensure_dirs()
        matrix = build_summary_matrix(verbose=verbose)
        print("OK: rebuilt summary_matrix")
        print("UPDATED:", SUMMARY_MATRIX_PATH)
        print("count_internal:", matrix.get("count_internal"))
        print("count_outfield:", matrix.get("count_outfield"))
        return

    if len(sys.argv) == 3 and sys.argv[1] == "--normalize-consumed":
        normalize_consumed(sys.argv[2])
        return

    if len(sys.argv) != 3:
        print("usage: python verify/accept_outfield_pass.py <input_json> <dest_name_without_ext>")
        print("   or: python verify/accept_outfield_pass.py --rebuild [--verbose]")
        print("   or: python verify/accept_outfield_pass.py --normalize-consumed <filename.json>")
        sys.exit(1)

    accept_one(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()