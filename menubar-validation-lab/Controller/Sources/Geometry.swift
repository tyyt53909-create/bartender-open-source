import Foundation

// Derived from MenubarHide a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960.
// Copyright (c) 2026 Sparrow. MIT; full notice in THIRD_PARTY_NOTICES.md.
// OUR guards refuse invalid topology, lost 64-point margin and shortfall.
// This is not an unmodified upstream build or a verified macOS backend.
struct DisplayGeometry {
    let width: Double
    let statusWidth: Double
}
struct GeometryPlan {
    let allowed: Bool
    let reason: String
    let unit: Double
    let activeSpacers: Int
    let coveredWidth: Double
    let requiredWidth: Double
    let minimumCliff: Double
    var json: [String: Any] {
        ["allowed": allowed, "reason": reason, "unit_points": unit,
         "active_spacers": activeSpacers, "covered_points": coveredWidth,
         "required_points": requiredWidth, "minimum_candidate_cliff_points": minimumCliff,
         "strategy": "guarded_candidate",
         "derived_from": "junior-rj/menubar-hide@a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960",
         "evidence_level": "geometry_model_only_not_macos_result"]
    }
}
enum CandidateGeometry {
    static let spacerCount = 6
    static func plan(_ displays: [DisplayGeometry]) -> GeometryPlan {
        func refused(_ reason: String) -> GeometryPlan {
            GeometryPlan(allowed: false, reason: reason, unit: 0, activeSpacers: 0,
                         coveredWidth: 0, requiredWidth: 0, minimumCliff: 0)
        }
        guard !displays.isEmpty else { return refused("no_display_topology") }
        guard displays.allSatisfy({
            $0.width.isFinite && $0.statusWidth.isFinite && $0.width > 0 &&
            $0.statusWidth > 0 && $0.statusWidth <= $0.width
        }) else { return refused("invalid_display_topology") }
        let cliff = displays.map {
            $0.statusWidth < $0.width ? $0.statusWidth * 0.75 : $0.width / 2
        }.min()!
        let widest = displays.map(\.statusWidth).max()!
        let unit = max(200, floor(cliff - 64))
        // Bound before converting Double to Int, including fuzz inputs.
        let needed = max(0, ceil(widest / unit) - 1)
        let active = Int(min(Double(spacerCount), needed))
        let covered = Double(active + 1) * unit
        let headroom = cliff - unit
        let reason: String
        if !covered.isFinite { return refused("nonfinite_geometry_result") }
        if unit >= cliff { reason = "candidate_unit_reaches_discard_cliff" }
        else if headroom < 64 { reason = "candidate_margin_below_64_points" }
        else if covered < widest { reason = "candidate_capacity_shortfall" }
        else { reason = "model_allows_experiment_not_verified" }
        return GeometryPlan(allowed: reason == "model_allows_experiment_not_verified", reason: reason,
                            unit: unit, activeSpacers: active, coveredWidth: covered,
                            requiredWidth: widest, minimumCliff: cliff)
    }
}

