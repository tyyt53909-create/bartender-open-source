public protocol InventoryProvider: Sendable {
    func observe() async -> ObservedState
}

public protocol VisibilityBackend: Sendable {
    func apply(action: VisibilityAction, to previewedDomain: AffectedDomain,
               ticket: OperationTicket) async -> VisibilityResult
}

public protocol AccessBackend: Sendable {
    func access(_ target: ExactTarget, action: AccessAction, ticket: OperationTicket) async -> AccessResult
}

/// Synchronous value transformation. Implementations may only use the supplied snapshots.
public protocol LayoutPlanner: Sendable {
    func plan(request: PlanningRequest, intent: UserIntent, observed: ObservedState, capabilities: [Capability],
              ticket: OperationTicket) -> PlanningResult
}
