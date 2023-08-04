package node.managers;

import java.util.LinkedList;
import java.util.stream.Collectors;
import node.job.Job;
import node.job.JobStatus;

public class JobManager {
    // Value holding the singleton instance of the Job Manager
    private static JobManager instance = null; 
    
    // LinkedList holding *all* Jobs (running or finished and yet to be cleaned up)
    private LinkedList<Job> jobs = null;
    
    // Mutex object to allow exclusive access to the "jobs" LinkedList
    private final Object jobsMutex = new Object();
    
    private JobManager() {
        this.jobs = new LinkedList<>();
    }
    
    public static JobManager getInstance() {
        // If there is no current instance of the Job Manager, create a new Instance
        if (instance != null) {
            return instance;
        }
        
        // Create a new instance of the Job Manager and store under "instance"
        instance = new JobManager();
        return instance;
    }
    
    public void startJob(int idNumber, int executionTime) {
        // Create a new Job object with the given Job ID Number and Execution Time
        Job job = new Job(idNumber, executionTime);
        
        // Acquire the "jobsMutex" Mutex and add the Job to the "jobs" LinkedList
        synchronized (jobsMutex) { jobs.add(job); }
        
        // Start the new Job's execution on a separate Thread
        job.start();
        System.out.printf("JobManager - INFO: Started Job %d with a %d second Execution Time\n", job.getIdNumber(), job.getExecutionTime());
    }
    
    public LinkedList<Job> getAllFinishedJobs() {
        // Create a new LinkedList to hold any finished Jobs
        LinkedList<Job> finishedJobs = null;
        
        // Acquire the "jobsMutex" Mutex and filter the LinkedList of jobs to find all Jobs with status == JobStatus.FINISHED
        synchronized(jobsMutex) {
            finishedJobs = jobs.stream()
                    .filter(job -> job.getStatus() == JobStatus.FINISHED)
                    .collect(Collectors.toCollection(LinkedList::new));
            
            // Remove all finished Jobs from the LinkedList of Jobs
            jobs.removeAll(finishedJobs);
        }
        
        // Return the LinkedList of all finished Jobs
        return finishedJobs;
    }
    
    public void stopAllRunningJobs() {
        // Aquire the "jobsMutex" Mutex
        synchronized(jobsMutex) {
            // Iterate through the jobs LinkedList and call the "stop" method if the Job's status == JobStatus.RUNNING
            for (Job job: jobs) {
                if (job.getStatus() == JobStatus.RUNNING) {
                    job.stop();
                    System.out.printf("JobManager - INFO: Stopped Job %d\n", job.getIdNumber());
                }
            }
        }
    }
    
}
