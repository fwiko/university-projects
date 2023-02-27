/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.job;

/**
 *
 * @author fwiko
 */
public class Job {
    private int jobId = 0;
    private int executionTime = 0;
    
    public Job(int jobId, int executionTime) {
        this.jobId = jobId;
        this.executionTime = executionTime;
    }
    
    public Integer getId() {
        return jobId;
    }
    
    public Integer getExecutionTime() {
        return executionTime;
    }
}
