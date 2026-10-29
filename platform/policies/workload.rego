
package sog.workload

import rego.v1

default decision := "deny"

authorized_domain if {
    input.identity.groups[_] == sprintf("%s-developers", [input.workload.domain])
}

nonprod_environment if {
    input.workload.environment == "nonprod"
}

valid_size if {
    input.workload.size in {"small", "medium", "large"}
}

requires_approval if {
    authorized_domain
    nonprod_environment
    input.workload.size == "large"
    count(input.workload.justification) > 0
}

decision := "allow" if {
    authorized_domain
    nonprod_environment
    valid_size
    input.workload.size in {"small", "medium"}
}

decision := "requires_approval" if {
    requires_approval
}