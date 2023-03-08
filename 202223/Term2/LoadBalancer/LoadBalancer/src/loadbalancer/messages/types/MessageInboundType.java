package loadbalancer.messages.types;

public enum MessageInboundType {
    REG_INITIATOR,
    REG_NODE,
    NEW_JOB,
    NEW_JOB_FAILURE,
    NEW_JOB_SUCCESS,
    FIN_JOB,
    ACK_IS_ALIVE,
    STOP_SYSTEM,
    GET_INFORMATION
}
