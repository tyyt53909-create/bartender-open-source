import Foundation

public enum VisibilityAction: Hashable, Sendable { case reveal, collect }
public enum AccessAction: Hashable, Sendable { case locate, openMenu, secondaryClick, optionClick }
public enum DisplayScope: Sendable { case single(String), shared([String]) }
public enum VisibilityDomain: Sendable {
    case individualItem(UUID)
    case application(ProducerIdentity, members: [UUID])
    case contiguousRange(orderedMembers: [UUID])
    case ownItems([UUID])
}

public struct AffectedDomain: Sendable {
    public let granularity: VisibilityDomain
    public let displays: DisplayScope

    public init(
        granularity: VisibilityDomain,
        displays: DisplayScope
    ) {
        self.granularity = granularity
        self.displays = displays
    }
}

public struct UserIntent: Sendable {
    public let userRevision: UInt64
    public let items: [LogicalItem]
    public let pinnedOrder: [UUID]
    public let collectedOrder: [UUID]

    public init(
        userRevision: UInt64,
        items: [LogicalItem],
        pinnedOrder: [UUID],
        collectedOrder: [UUID]
    ) {
        self.userRevision = userRevision
        self.items = items
        self.pinnedOrder = pinnedOrder
        self.collectedOrder = collectedOrder
    }
}

public struct OperationTicket: Equatable, Sendable {
    public let id: UUID
    public let generation: UInt64
    public let userRevision: UInt64
    public let inventoryEpoch: UInt64
    public let permissionEpoch: UInt64
    public let topologyEpoch: UInt64

    public init(
        id: UUID,
        generation: UInt64,
        userRevision: UInt64,
        inventoryEpoch: UInt64,
        permissionEpoch: UInt64,
        topologyEpoch: UInt64
    ) {
        self.id = id
        self.generation = generation
        self.userRevision = userRevision
        self.inventoryEpoch = inventoryEpoch
        self.permissionEpoch = permissionEpoch
        self.topologyEpoch = topologyEpoch
    }
}

extension OperationTicket {
    public func isCurrent(active: Self?) -> Bool { active == self }
}

public enum ItemAction: Hashable, Sendable {
    case discover, visibility(VisibilityAction), access(AccessAction)
}
public enum CapabilityLevel: Sendable { case verified, experimental, unsupported, unknown }

public struct Capability: Sendable {
    public let osBuild: String
    public let hardwareClass: String
    public let backendRevision: String
    public let permissionMode: String
    public let topologyScope: String
    public let itemID: UUID
    public let action: ItemAction
    public let domain: AffectedDomain
    public let level: CapabilityLevel
    public let evidenceReference: String?

    public init(
        osBuild: String,
        hardwareClass: String,
        backendRevision: String,
        permissionMode: String,
        topologyScope: String,
        itemID: UUID,
        action: ItemAction,
        domain: AffectedDomain,
        level: CapabilityLevel,
        evidenceReference: String?
    ) {
        self.osBuild = osBuild
        self.hardwareClass = hardwareClass
        self.backendRevision = backendRevision
        self.permissionMode = permissionMode
        self.topologyScope = topologyScope
        self.itemID = itemID
        self.action = action
        self.domain = domain
        self.level = level
        self.evidenceReference = evidenceReference
    }
}

public enum PlanningRequest: Sendable {
    case organize
    case access(itemID: UUID, action: AccessAction)
    case recover([MutationRecord])
}

public enum PlanStep: Sendable {
    case visibility(domain: AffectedDomain, action: VisibilityAction, expected: Visibility)
    case access(target: ExactTarget, action: AccessAction, expected: AccessExpectation)
}
public enum AccessExpectation: Sendable { case located, nativeMenuOpen }
public enum PlanningResult: Sendable { case ready(EffectivePlan), held(reason: String) }

public struct EffectivePlan: Sendable {
    public let ticket: OperationTicket
    public let affectedDomain: AffectedDomain
    public let requiredCapabilities: [Capability]
    public let steps: [PlanStep]

    public init(
        ticket: OperationTicket,
        affectedDomain: AffectedDomain,
        requiredCapabilities: [Capability],
        steps: [PlanStep]
    ) {
        self.ticket = ticket
        self.affectedDomain = affectedDomain
        self.requiredCapabilities = requiredCapabilities
        self.steps = steps
    }
}

public struct LayoutFingerprint: Equatable, Sendable {
    public let orderedMembers: [UUID]
    public let visibleMembers: [UUID]
    public let precedingNeighbor: UUID?
    public let followingNeighbor: UUID?

    public init(
        orderedMembers: [UUID],
        visibleMembers: [UUID],
        precedingNeighbor: UUID?,
        followingNeighbor: UUID?
    ) {
        self.orderedMembers = orderedMembers
        self.visibleMembers = visibleMembers
        self.precedingNeighbor = precedingNeighbor
        self.followingNeighbor = followingNeighbor
    }
}

public enum MutationStatus: Sendable { case owned, relinquished, unresolved, restored }

public struct MutationRecord: Sendable {
    public let owner: OperationTicket
    public let domain: AffectedDomain
    public let before: LayoutFingerprint
    public let applied: LayoutFingerprint
    public let status: MutationStatus

    public init(
        owner: OperationTicket,
        domain: AffectedDomain,
        before: LayoutFingerprint,
        applied: LayoutFingerprint,
        status: MutationStatus
    ) {
        self.owner = owner
        self.domain = domain
        self.before = before
        self.applied = applied
        self.status = status
    }
}

public enum AccessResult: Sendable {
    case located(ExactTarget, Presentation, observationRevision: UInt64)
    case actionSubmitted(OperationTicket)
    case observedMenuOpen(ExactTarget, evidence: Observation<String>)
    case requiresTemporaryLayout(AffectedDomain)
    case ambiguous([RuntimeBinding])
    case blocked(reason: String)
    case unsupported(reason: String)
    case outcomeUnknown(OperationTicket, reason: String)
}
public enum VisibilityResult: Sendable {
    case observed(Observation<Visibility>)
    case submitted, blocked(reason: String), unsupported(reason: String), unknown(reason: String)
}
public enum StepResult: Sendable { case visibility(VisibilityResult), access(AccessResult) }

public struct OperationReceipt: Sendable {
    public let ticket: OperationTicket
    public let attempted: PlanStep
    public let result: StepResult
    public let confirmedMutations: [MutationRecord]

    public init(
        ticket: OperationTicket,
        attempted: PlanStep,
        result: StepResult,
        confirmedMutations: [MutationRecord]
    ) {
        self.ticket = ticket
        self.attempted = attempted
        self.result = result
        self.confirmedMutations = confirmedMutations
    }
}
