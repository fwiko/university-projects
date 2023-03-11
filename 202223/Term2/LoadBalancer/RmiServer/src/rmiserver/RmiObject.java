package rmiserver;

import java.rmi.*;
import java.rmi.server.*;

public class RmiObject extends UnicastRemoteObject implements RmiObjectInterface {

    String data = "from rmi object";

    public RmiObject() throws RemoteException {
    }

    public String getReply() throws RemoteException {
        return this.data;
    }

    public void setData( String theData ) {
        this.data = theData;
    }

}
