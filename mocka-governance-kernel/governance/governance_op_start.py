# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_op_start.py
# note: Phase14.6 Roadmap-3 Operation start event

from governance_writer import append_event

def main():
    payload = {
        "phase": "14.6",
        "decl": "Governance operations started",
        "human_docs_initialized": True
    }
    note = "note: Phase14.6 OPERATION_START (DOG/CSV initialized)"
    event_id = append_event("OPERATION_START", payload, note)
    print("OK: appended OPERATION_START")
    print("EVENT_ID:", event_id)

if __name__ == "__main__":
    main()