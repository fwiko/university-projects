/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.managers;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;
import loadbalancer.job.Job;
import loadbalancer.node.Node;

/**
 *
 * @author fwiko
 */
public class JobManager {
    private static JobManager instance;
    
    private final LinkedList<Job> jobQueue;
    private final ArrayList<Job> allocatedJobs;
    
    // Mutexes used for exclusive access to jobQueue and allocatedJobs
    private final Object jobQueueLock = new Object();
    private final Object allocatedJobsLock = new Object();
    
    // Message manager singleton class instance
    private final MessageManager messageManager;
    
    // Next Job ID to assign to a Job
    private int nextJobId = 1;
    
    private JobManager() {
        this.jobQueue = new LinkedList<>();
        this.allocatedJobs = new ArrayList<>();
        this.messageManager = MessageManager.getInstance();
    }

    public static JobManager getInstance() {
        // If the JobManager instance already exists, return the instance
        if (instance != null) {
            return instance;
        }
        // If the JobManager instance does not exist, create a new instance
        instance = new JobManager();
        return instance;
    }

    public Job queueNewJob(int executionTime) {
        // Create a new Job object
        Job newJob = new Job(nextJobId, executionTime);
        
        // Add the new Job object to the Job queue LinkedList
        synchronized (jobQueueLock) {
            jobQueue.add(newJob);
        }
        
        // Increment the next Job ID value
        nextJobId += 1;
        
        return newJob;
    }
    
    public void allocateJob(Job job, Node node) {
        // Add the new Job allocation to the LinkedHashMap of allocated Jobs
        synchronized (allocatedJobsLock) {
            synchronized (jobQueueLock) {
                jobQueue.remove(job);
            }
            allocatedJobs.add(job);
            job.setHandlerNodeId(node.getIdNum());
        }
    }
    

    public void deallocateJob(Job job) {
        synchronized (allocatedJobsLock) {
            // Remove the specified Job from the allocatedJobs ArrayList
            allocatedJobs.remove(job);
        }
    }
    
    public Job getAllocatedJobById(int jobIdNumber) {
        synchronized (allocatedJobsLock) {
            for (Job job : allocatedJobs) {
                if (job.getIdNumber() == jobIdNumber) {
                    return job;
                }
            }
        }
        return null;
    }
    
    public Job getNextJob() {
        synchronized (jobQueueLock) {
            // Fetch (don't remove) the first element of the jobQueue LinkedList
            return jobQueue.peekFirst();
        }
    }
    
    public List getNodeJobs(Node node) {
        synchronized (allocatedJobsLock) {
            // Return a filtered List of Jobs containing only those allocated to the specified Node
            return allocatedJobs
                    .stream()
                    .filter(allocJob -> allocJob.getHandlerNodeId() == node.getIdNum())
                    .collect(Collectors.toList());
        }
    }
    
    public int getNumberOfNodeJobs(Node node) {
        // Return the number of Jobs allocated to the specified Node
        return getNodeJobs(node).size();
    }
}
