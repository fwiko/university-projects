/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer;

import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

/**
 *
 * @author fwiko
 */
public class Server {
    private int portNumber = 0;
    private InetAddress ipAddress = null;
    
    private DatagramSocket socket = null;
    
    public Server(String ipAddress, int portNumber) {
        setIpAddress(ipAddress);
        setPortNumber(portNumber);
    }
        
    public void start() {
        try {
            socket = new DatagramSocket(portNumber);
            socket.setSoTimeout(0);
        } catch (SocketException e) {
            System.err.println("Error: Failed to create new Socket.");
            System.exit(0);
        }
        
        recieveMessages(socket);
    }

    private void recieveMessages(DatagramSocket socket) {
        //
    }
    
    private void setIpAddress(String ipAddress) throws IllegalArgumentException {
        try {
            this.ipAddress = InetAddress.getByName(ipAddress);
        } catch (UnknownHostException e) {
            throw new IllegalArgumentException(String.format(
                    "Error: IP Address \"%s\" is not recognised.",
                    ipAddress
            ));
        }
    }
    
    private void setPortNumber(int portNumber) throws IllegalArgumentException {
        if (portNumber < 1 || portNumber >= 65535) {
            throw new IllegalArgumentException(String.format(
                    "Error: Port \"%s\" is outside of the valid range.", 
                    portNumber
            ));
        } else {
            this.portNumber = portNumber;
        }
    }
}
