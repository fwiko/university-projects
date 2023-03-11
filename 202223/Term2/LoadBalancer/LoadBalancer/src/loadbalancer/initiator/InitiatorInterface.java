package loadbalancer.initiator;

import java.rmi.*;

public interface InitiatorInterface extends Remote {
    public void addNewJob(int executionTime) throws RemoteException;
    public String getSummary() throws RemoteException;
}
