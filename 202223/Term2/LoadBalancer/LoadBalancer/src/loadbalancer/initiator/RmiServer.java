package loadbalancer.initiator;

import java.rmi.AlreadyBoundException;
import java.rmi.registry.Registry;
import java.rmi.registry.LocateRegistry;
import java.rmi.RemoteException;
//import java.rmi.NoSuchObjectException;

public class RmiServer {
    private Registry rmiRegistry = null;
    private int portNumber = 0;
    
    public RmiServer(int portNumber) throws RemoteException {
        this.portNumber = portNumber;
    }
    
    public void start() {
        
        try {
            rmiRegistry = LocateRegistry.createRegistry(portNumber);
            
            rmiRegistry.bind("Initiator", new Initiator());
        } catch (RemoteException | AlreadyBoundException exception) {
            System.err.printf("InitiatorRmiServer - ERROR: Failed to bind to InitiatorRmiObject (%s)\n", exception.getMessage());
            System.exit(-1);
        }
    }

}
