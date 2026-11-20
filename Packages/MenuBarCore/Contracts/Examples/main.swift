import Foundation
import MenuBarContracts

let itemID = UUID()
let lifetime = UUID()
let first = RuntimeBinding(handle: UUID(), hostLifetime: lifetime, inventoryEpoch: 1)
let second = RuntimeBinding(handle: UUID(), hostLifetime: lifetime, inventoryEpoch: 1)
let instant = Date(timeIntervalSince1970: 0)

func observation<T>(_ value: T?, freshness: Freshness = .fresh,
                    completeness: Completeness = .complete) -> Observation<T> {
    Observation(value: value, source: .accessibility, observedAt: instant,
                freshness: freshness, completeness: completeness)
}

let inventory = [first, second].map {
    ObservedItem(binding: $0, producer: nil, stableIdentifier: "duplicate", role: "menu extra",
                 presentations: [], visibility: observation(.unknown), dynamicValue: observation(nil))
}

func snapshot(_ revision: UInt64, freshness: Freshness = .fresh,
              completeness: Completeness = .complete) -> ObservedState {
    ObservedState(inventory: observation(inventory, freshness: freshness, completeness: completeness),
                  inventoryEpoch: 1, topologyEpoch: 1, observationRevision: revision)
}

func target(_ resolution: IdentityResolution, _ state: ObservedState) -> ExactTarget? {
    ExactTarget(itemID: itemID, resolution: resolution, state: state)
}

let initial = snapshot(1)
for candidates in [[first, second], [second, first]] {
    precondition(target(.ambiguous(candidates), initial) == nil)
}
print("ambiguous duplicate identifiers / both candidate orders -> refused")
precondition(target(.unknown, initial) == nil && target(.unmatched, initial) == nil)
precondition(target(.unique(first), snapshot(1, freshness: .stale)) == nil)
precondition(target(.unique(first), snapshot(1, completeness: .partial)) == nil)
print("unknown, unmatched, stale or incomplete inventory -> refused")

// Here the resolver has independently revalidated the same live binding.
precondition(target(.unique(first), initial)?.binding == first)
let operation = UUID()
func ticket(id: UUID = operation, generation: UInt64 = 1, user: UInt64 = 1,
            inventory: UInt64 = 1, permission: UInt64 = 1, topology: UInt64 = 1) -> OperationTicket {
    OperationTicket(id: id, generation: generation, userRevision: user, inventoryEpoch: inventory,
                    permissionEpoch: permission, topologyEpoch: topology)
}

let issued = ticket()
let refreshed = snapshot(2)
precondition(refreshed.observationRevision != initial.observationRevision)
precondition(issued.isCurrent(active: ticket(inventory: refreshed.inventoryEpoch, topology: refreshed.topologyEpoch)))
print("display refresh with unchanged binding and epochs -> ticket current")
let invalidations: [(String, OperationTicket?)] = [
    ("replacement operation", ticket(id: UUID())), ("external layout change", ticket(generation: 2)),
    ("user edit", ticket(user: 2)), ("target relaunched", ticket(inventory: 2)),
    ("permission withdrawn", ticket(permission: 2)), ("display changed", ticket(topology: 2)),
    ("cancelled", nil)
]
for (event, active) in invalidations {
    precondition(!issued.isCurrent(active: active))
    print("\(event) -> old ticket refused")
}
