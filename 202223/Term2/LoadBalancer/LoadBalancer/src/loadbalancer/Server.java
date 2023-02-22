/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer;

/**
 *
 * @author fwiko
 */
public class Server {
    private int port = 0;
    
    public Server(int port) {
        this.port = port;
    }
    
    public void start() {
        if (port < 1 || port >= 65535) {
            throw new IllegalArgumentException("Error: Port \"" + port + "\" is outside of the valid range.");
        }
        System.out.println("Done");
    }
}
