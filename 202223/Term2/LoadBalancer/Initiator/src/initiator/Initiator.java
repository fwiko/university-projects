/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package initiator;

import initiator.messages.MessageOutbound;
import initiator.messages.types.MessageOutboundType;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

/**
 *
 * @author fwiko
 */
public class Initiator {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        InetAddress ipAddress = null;
        try {
            ipAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            System.err.println("Error: Failed to get LocalHost address.");
            System.exit(0);
        }
        
        int port = 4000;
        int recPort = 2512;
        
        DatagramSocket socket;
        try {
            socket = new DatagramSocket(2512);
        } catch (SocketException e) {
            e.printStackTrace();
            return;}

        InetAddress initiatorIpAddress;
        try {
            initiatorIpAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            e.printStackTrace();
            return;
        }
        
        InitiatorClient initiatorClient = new InitiatorClient();
        initiatorClient.start(initiatorIpAddress, recPort, initiatorIpAddress, recPort);
        
    }
    
}
