# A latency number for the tree

Type: task
Status: open
Blocked by: -
Parent: ../map.md

## Question

Raised by ticket 06. The map bans reading a production or shared drive, and the
research honoured that - so it returned a correctly shaped implementation shortlist
with no numbers in it.

Neither Microsoft nor Google publishes a latency figure for enumerating a directory
on a network-backed virtual drive. Microsoft says only that it "will be more
expensive than normal". That means the tree cannot currently be given:

- a spinner threshold - at what delay does a node expansion show a loading state
- a lazy-load budget - how many nodes may be prefetched ahead of the cursor
- a count cap - where "n+" replaces a real number
- a cache TTL - how long an enumeration stays trustworthy

Every one of those is a number, and none can come from documentation.

Do the work that produces one. Two routes, and the choice is the user's:

1. **Provision a synthetic fixture.** A throwaway Google Workspace shared drive,
   populated to resemble a real studio drive, mounted through Drive for Desktop.
   Costs a Workspace seat and setup time. Safe, repeatable, and reusable as a test
   fixture for the rest of this effort.
2. **Authorise a one-off read of the studio drive.** A read-only enumeration
   benchmark - no writes, no opens, `os.scandir` only - against a small number of
   real projects. Cheaper, faster, and needs explicit permission because it breaks
   the map's standing constraint.

Resolved when a measurement exists and the four numbers above are written down with
the conditions they were taken under. Record them where the tree implementation will
read them, not only in this ticket.
