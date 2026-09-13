## Global work ledger

A cross-session work ledger — a live database of sessions and events — is held
by the BotBeam ledger service (`/ledger` API); its protocol is the `ledger`
skill. When significant work completes in any session — a deliverable ships, a
decision is made, an artifact is produced or sent — invoke the ledger skill and
log it. When asked what's going on, what happened recently, or about an ongoing
workstream, consult the ledger first.
