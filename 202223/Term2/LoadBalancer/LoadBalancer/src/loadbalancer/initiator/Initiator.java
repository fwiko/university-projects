package loadbalancer.initiator;

import java.rmi.*;
import java.rmi.server.*;
//import loadbalancer.managers.JobManager;
//import loadbalancer.managers.NodeManager;

public class Initiator extends UnicastRemoteObject implements InitiatorInterface {
    
//    private JobManager jobManager = null;
//    private NodeManager nodeManager = null;
    
    public Initiator() throws RemoteException {
//        jobManager = JobManager.getInstance();
//        nodeManager = NodeManager.getInstance();
    }
    
    public void addNewJob(int executionTime) throws RemoteException {
//        jobManager.addNewJob(executionTime);
    }

    public String getSummary() throws RemoteException {
        return null;
    }
    
}
