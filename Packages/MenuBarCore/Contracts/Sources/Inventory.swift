import Foundation

public struct ProducerIdentity: Sendable {
    public let bundleID: String?
    public let verifiedPath: String?
    public let signingIdentifier: String?

    public init(
        bundleID: String?,
        verifiedPath: String?,
        signingIdentifier: String?
    ) {
        self.bundleID = bundleID
        self.verifiedPath = verifiedPath
        self.signingIdentifier = signingIdentifier
    }
}

public struct LogicalItem: Sendable {
    public let id: UUID
    public let producer: ProducerIdentity?
    public let stableIdentifier: String?
    public let confirmedMappingID: UUID?
    public let alias: String?

    public init(
        id: UUID,
        producer: ProducerIdentity?,
        stableIdentifier: String?,
        confirmedMappingID: UUID?,
        alias: String?
    ) {
        self.id = id
        self.producer = producer
        self.stableIdentifier = stableIdentifier
        self.confirmedMappingID = confirmedMappingID
        self.alias = alias
    }
}

public struct RuntimeBinding: Hashable, Sendable {
    public let handle: UUID
    public let hostLifetime: UUID
    public let inventoryEpoch: UInt64

    public init(
        handle: UUID,
        hostLifetime: UUID,
        inventoryEpoch: UInt64
    ) {
        self.handle = handle
        self.hostLifetime = hostLifetime
        self.inventoryEpoch = inventoryEpoch
    }
}

public enum Freshness: Sendable { case fresh, stale, unknown }
public enum Completeness: Sendable { case complete, partial, unknown }
public enum ObservationSource: Sendable { case accessibility, systemInventory, ownControl, userConfirmation, unknown }
public enum Visibility: Sendable { case configuredVisible, observedInBar, observedInOverflow, offscreen, unknown }

public struct Observation<Value: Sendable>: Sendable {
    public let value: Value?
    public let source: ObservationSource
    public let observedAt: Date
    public let freshness: Freshness
    public let completeness: Completeness

    public init(
        value: Value?,
        source: ObservationSource,
        observedAt: Date,
        freshness: Freshness,
        completeness: Completeness
    ) {
        self.value = value
        self.source = source
        self.observedAt = observedAt
        self.freshness = freshness
        self.completeness = completeness
    }
}

public struct Presentation: Sendable {
    public let displayID: String
    public let x: Double
    public let y: Double
    public let width: Double
    public let height: Double
    public let coordinateSpace: String
    public let unit: String
    public let scale: Double
    public let topologyEpoch: UInt64
    public let observedAt: Date

    public init(
        displayID: String,
        x: Double,
        y: Double,
        width: Double,
        height: Double,
        coordinateSpace: String,
        unit: String,
        scale: Double,
        topologyEpoch: UInt64,
        observedAt: Date
    ) {
        self.displayID = displayID
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.coordinateSpace = coordinateSpace
        self.unit = unit
        self.scale = scale
        self.topologyEpoch = topologyEpoch
        self.observedAt = observedAt
    }
}

public struct ObservedItem: Sendable {
    public let binding: RuntimeBinding
    public let producer: ProducerIdentity?
    public let stableIdentifier: String?
    public let role: String?
    public let presentations: [Presentation]
    public let visibility: Observation<Visibility>
    public let dynamicValue: Observation<String>

    public init(
        binding: RuntimeBinding,
        producer: ProducerIdentity?,
        stableIdentifier: String?,
        role: String?,
        presentations: [Presentation],
        visibility: Observation<Visibility>,
        dynamicValue: Observation<String>
    ) {
        self.binding = binding
        self.producer = producer
        self.stableIdentifier = stableIdentifier
        self.role = role
        self.presentations = presentations
        self.visibility = visibility
        self.dynamicValue = dynamicValue
    }
}

public struct ObservedState: Sendable {
    public let inventory: Observation<[ObservedItem]>
    public let inventoryEpoch: UInt64
    public let topologyEpoch: UInt64
    public let observationRevision: UInt64

    public init(
        inventory: Observation<[ObservedItem]>,
        inventoryEpoch: UInt64,
        topologyEpoch: UInt64,
        observationRevision: UInt64
    ) {
        self.inventory = inventory
        self.inventoryEpoch = inventoryEpoch
        self.topologyEpoch = topologyEpoch
        self.observationRevision = observationRevision
    }
}

public enum IdentityResolution: Sendable {
    case unique(RuntimeBinding)
    case ambiguous([RuntimeBinding])
    case unmatched
    case unknown
}

// A resolver supplies the candidates. This gate only admits a current, unique binding.
public struct ExactTarget: Sendable {
    public let itemID: UUID
    public let binding: RuntimeBinding

    public init?(itemID: UUID, resolution: IdentityResolution, state: ObservedState) {
        guard case let .unique(binding) = resolution,
              binding.inventoryEpoch == state.inventoryEpoch,
              state.inventory.freshness == .fresh,
              state.inventory.completeness == .complete,
              let items = state.inventory.value,
              items.filter({ $0.binding == binding }).count == 1 else { return nil }
        self.itemID = itemID
        self.binding = binding
    }
}
