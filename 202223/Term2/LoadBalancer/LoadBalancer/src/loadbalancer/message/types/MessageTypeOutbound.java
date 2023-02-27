/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.message.types;

/**
 *
 * @author fwiko
 */
public enum MessageTypeOutbound {
    REG_INITIATOR_FAILURE,
    REG_INITIATOR_SUCCESS,
    REG_NODE_FAILURE,
    REG_NODE_SUCCESS,
    NEW_JOB,
    FIN_JOB,
}
