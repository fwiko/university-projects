/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.job;

public class Job {
    // Job information properties
    private int jobIdNumber = 0;
    private int executionTime = 0;
    
    // Node allocation information
    private int handlerNodeId = -1;
    
    public Job(int jobIdNumber, int executionTime) {
        this.jobIdNumber = jobIdNumber;
        this.executionTime = executionTime;
    }
    
    public int getIdNumber() {
        return jobIdNumber;
    }
    
    public int getExecutionTime() {
        return executionTime;
    }
    
    public void setHandlerNodeId(int nodeId) {
        this.handlerNodeId = nodeId;
    }
    
    public int getHandlerNodeId() {
        return handlerNodeId;
    }
}
