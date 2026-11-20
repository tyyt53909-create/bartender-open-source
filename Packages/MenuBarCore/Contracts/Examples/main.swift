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
let resolvedA = IdentityResolution.unique(itemID: itemID, binding: first)
precondition(ExactTarget(itemID: UUID(), resolution: resolvedA, state: initial) == nil)
print("resolution for A used to request B -> refused")
for candidates in [[first, second], [second, first]] {
    precondition(target(.ambiguous(candidates), initial) == nil)
}
print("ambiguous duplicate identifiers / both candidate orders -> refused")
precondition(target(.unknown, initial) == nil && target(.unmatched, initial) == nil)
precondition(target(resolvedA, snapshot(1, freshness: .stale)) == nil)
precondition(target(resolvedA, snapshot(1, completeness: .partial)) == nil)
print("unknown, unmatched, stale or incomplete inventory -> refused")

// Here the resolver has independently revalidated the same live binding.
precondition(target(resolvedA, initial)?.binding == first)
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

// This fixture controls one backend response. Both state changes and the resumed
// client run on the main actor, so the ordering needs no timers or polling.
@MainActor
final class PendingResponse {
    private var suspended: CheckedContinuation<Void, Never>?
    private var waiter: CheckedContinuation<Void, Never>?

    func suspend() async {
        await withCheckedContinuation { continuation in
            suspended = continuation
            waiter?.resume()
            waiter = nil
        }
    }

    func waitUntilSuspended() async {
        if suspended == nil {
            await withCheckedContinuation { waiter = $0 }
        }
    }

    func resume() {
        precondition(suspended != nil)
        suspended?.resume()
        suspended = nil
    }
}

@MainActor
final class ExampleConsumer {
    var active: OperationTicket?
    private(set) var receipts: [OperationReceipt] = []
    private(set) var followUpActions = 0

    init(active: OperationTicket) { self.active = active }

    func consume(ticket: OperationTicket, step: VisibilityStep, response: VisibilityResult,
                 pending: PendingResponse) async {
        guard ticket.isCurrent(active: active) else { return }
        await pending.suspend()
        guard ticket.isCurrent(active: active),
              let record = MutationRecord(owner: ticket, active: active, step: step, result: response)
        else { return }
        receipts.append(OperationReceipt(ticket: ticket, attempted: .visibility(step),
                                         result: .visibility(response), confirmedMutations: [record]))
        followUpActions += 1
    }
}

let otherID = UUID()
let members = [itemID, otherID]
let approved = AffectedDomain(granularity: .contiguousRange(orderedMembers: members), displays: .single("main"))
let neighbor = UUID()
func layout(_ visibility: Visibility, preceding: UUID?) -> DisplayLayouts {
    ["main": LayoutFingerprint(orderedMembers: members,
                               visibilityByMember: [itemID: visibility, otherID: visibility],
                               precedingNeighbor: preceding, followingNeighbor: nil)]
}
func sample(_ revision: UInt64, _ layouts: DisplayLayouts, completeness: Completeness = .complete) -> LayoutSample {
    LayoutSample(domain: approved, revision: revision, layouts: observation(layouts, completeness: completeness))
}
let before = layout(.observedInOverflow, preceding: neighbor)
let expected = layout(.observedInBar, preceding: neighbor)
let step = VisibilityStep(action: .reveal, before: sample(1, before), expected: expected)!
let movedNeighbor = layout(.observedInBar, preceding: UUID())
let unchangedTicket = ExampleConsumer(active: issued)
let changedLayout = ExampleConsumer(active: issued)
let replacedTicket = ExampleConsumer(active: issued)

@MainActor
func deliver(_ result: VisibilityResult, to consumer: ExampleConsumer, replaceTicket: Bool) async {
    let pending = PendingResponse()
    let task = Task {
        await consumer.consume(ticket: issued, step: step, response: result, pending: pending)
    }
    await pending.waitUntilSuspended()
    if replaceTicket { consumer.active = ticket(generation: 2) }
    pending.resume()
    await task.value
}

await deliver(.observed(sample(2, expected)), to: replacedTicket, replaceTicket: true)
precondition(!issued.isCurrent(active: replacedTicket.active))
precondition(replacedTicket.receipts.isEmpty && replacedTicket.followUpActions == 0)
print("ticket replaced while suspended -> resumed old callback: 0 receipts, 0 follow-up actions")

await deliver(.observed(sample(2, expected)), to: unchangedTicket, replaceTicket: false)
precondition(issued.isCurrent(active: unchangedTicket.active))
precondition(unchangedTicket.receipts.count == 1 && unchangedTicket.followUpActions == 1)
let confirmed = unchangedTicket.receipts[0].confirmedMutations[0]
precondition(confirmed.before == before && confirmed.applied == expected && confirmed.status == .owned)
print("fresh approved layout matched members, visibility and neighbors -> applied recorded, ticket current")

await deliver(.observed(sample(2, movedNeighbor)), to: changedLayout, replaceTicket: false)
precondition(issued.isCurrent(active: changedLayout.active))
precondition(changedLayout.receipts.isEmpty && changedLayout.followUpActions == 0)
print("same visibility, user replaced neighbor -> stopped, 0 claimed mutations, 0 follow-up actions")
for insufficient in [sample(1, expected), sample(2, expected, completeness: .partial)] {
    precondition(MutationRecord(owner: issued, active: issued, step: step, result: .observed(insufficient)) == nil)
}
print("replayed or partial observation -> 0 claimed mutations")
