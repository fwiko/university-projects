/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.managers;

import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;
import loadbalancer.job.Job;
import loadbalancer.message.MessageOutbound;
import loadbalancer.message.types.MessageTypeOutbound;
import loadbalancer.node.Node;

/**
 *
 * @author fwiko
 */
public class JobManager {
    private static JobManager instance;
    
    private final LinkedList<Job> jobQueue;
    private final LinkedHashMap<Job, Integer> allocatedJobs;
    
    // Mutexes used for exclusive access to jobQueue and allocatedJobs
    private final Object queueMutexLock = new Object();
    private final Object allocMutexLock = new Object();
    
    private final MessageManager messageManager;
    
    private int nextJobId = 1;
    
    private JobManager() {
        this.jobQueue = new LinkedList<>();
        this.allocatedJobs = new LinkedHashMap<>();
        
        this.messageManager = MessageManager.getInstance();
    }

    public static JobManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new JobManager();
        return instance;
    }
    

    public void queueJob(int executionTime) {
        // Create a new Job object
        Job newJob = new Job(nextJobId, executionTime);
        
        // Add the new Job object to the Job queue LinkedList
        synchronized (queueMutexLock) {
            jobQueue.add(newJob);
        }
        
        // Increment the next Job ID value
        nextJobId += 1;
    }
    
    public void allocateJob(Job job, Node node) {
        // Add the new Job allocation to the LinkedHashMap of allocated Jobs
        synchronized (allocMutexLock) {
            allocatedJobs.put(job, node.getIdNum());
        }
        
        // Send the Job allocation Message to the Node
        MessageOutbound newJobMessage = new MessageOutbound(MessageTypeOutbound.UNKNOWN, ",", job.getId().toString(), job.getExecutionTime().toString());
        messageManager.sendMessage(newJobMessage, node.getIpAddr(), node.getPortNum());
    }
    

    public void deallocateJob(Job job) {
        allocatedJobs.remove(job);
    }
    
    public void deallocateJobById(int jobId) {
        
    }
    
    public Job getNextJob() {
        // Fetch, Return, and Remove the first element of the Job queue
        synchronized (queueMutexLock) {
            return jobQueue.pollFirst();
        }
    }
    
    public int getNumberOfNodeJobs(Node node) {
        // Return the number of Jobs allocated to a specific Node
        return getNodeJobs(node).size();
    }
    
    
    public List getNodeJobs(Node node) {
        // Return a list of Jobs allocated to a specific Node
        return allocatedJobs
                .entrySet()
                .stream()
                .filter(allocation -> allocation.getValue().equals(node.getIdNum()))
                .collect(Collectors.toList());
    }
}
