/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.messages.types;

/**
 *
 * @author fwiko
 */
public enum MessageInboundType {
    REG_INITIATOR,
    REG_NODE,
    NEW_JOB,
    FIN_JOB,
    ACK_IS_ALIVE,
    EXITED_NODE,
    STOP_SYSTEM,
}
