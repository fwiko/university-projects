package loadbalancer.messages.types;

public enum MessageInboundType {
    ACK_IS_ALIVE,
    FIN_JOB,
    NEW_JOB_FAILURE,
    NEW_JOB_SUCCESS,
    REG_NODE,
    NEW_JOB,
    REG_CONTROLLER,
    STOP_SYSTEM,
    GET_INFO
}
