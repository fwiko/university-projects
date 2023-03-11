package loadbalancer.messages.types;

public enum MessageOutboundType {
    REG_SUCCESS,
    REG_FAILURE,
    IS_ALIVE,
    NEW_JOB,
    STOP_NODE,
    FIN_JOB,
    NEW_JOB_SUCCESS,
    NEW_JOB_FAILURE,
    INFO
}
