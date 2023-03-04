package loadbalancer.messages.types;

public enum MessageOutboundType {
    REG_INITIATOR_FAILURE,
    REG_INITIATOR_SUCCESS,
    REG_NODE_FAILURE,
    REG_NODE_SUCCESS,
    NEW_JOB,
    NEW_JOB_SUCCESS,
    NEW_JOB_FAILURE,
    FIN_JOB,
    IS_ALIVE,
    STOP_NODE,
    INFORMATION
}
