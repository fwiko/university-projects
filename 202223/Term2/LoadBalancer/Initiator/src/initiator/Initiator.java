/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package initiator;

import initiator.message.MessageOutbound;
import initiator.message.types.MessageTypeOutbound;
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
        
        byte[] buffer = new byte[1024];
        
        MessageOutbound message = new MessageOutbound(MessageTypeOutbound.STOP_SYSTEM, ",", ipAddress.getHostAddress(), String.valueOf(recPort));
        buffer = message.packString(",").getBytes();
        
        InetAddress initiatorIpAddress;
        try {
            initiatorIpAddress = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            e.printStackTrace();
            return;
        }
        
        DatagramPacket packet = new DatagramPacket(buffer, buffer.length, initiatorIpAddress, port);
        System.out.println("Sender: Ready to send on " + socket.getLocalAddress().toString() + " port: " + socket.getLocalPort());

        try {
            socket.send(packet);
        } catch (IOException e) {
            
        }
    }
    
}
