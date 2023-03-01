package node.managers;

import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;
import node.job.Job;
import node.job.JobStatus;

public class JobManager {
    // Singleton instance of JobManager
    private static JobManager instance;
    
    // LinkedLink of all Job objects being executed or yet to be returned
    private final LinkedList<Job> jobs;
    
    // Mutex object used for exclusive access to jobs LinkedList
    private final Object jobsLock = new Object();
    
    private JobManager() {
        this.jobs = new LinkedList<>();
    }

    public static JobManager getInstance() {
        // If an instance of the JobManager already exists
        if (instance != null) {
            return instance;
        }
        // Create a new instance of the JobManager
        instance = new JobManager();
        return instance;
    }
    
    public void startJob(int jobIdNumber, int jobExectutionTime) {
        // Create a new Job object with the specified ID Number and Execution Time
        Job newJob = new Job(jobIdNumber, jobExectutionTime);
        
        // Activate (Lock) the jobs LinkedList Mutex object
        synchronized (jobsLock) {
            // Add the new Job object to the jobs LinkedList
            jobs.add(newJob);
        }
        
        // Start the new Job's "workload" execution
        newJob.start();
        System.out.printf("JobManager - INFO: Started Job %d with Execution Time of %d seconds\n", jobIdNumber, jobExectutionTime);
    }
    
    public List<Job> getFinishedJobs() {
        List<Job> finishedJobs = null;
        
        // Activate (Lock) the jobs LinkedList Mutex object
        synchronized (jobsLock) {
            // Use a collector to get all Job objects with a status FINISHED
            finishedJobs = jobs
                    .stream()
                    .filter(job -> job.getStatus() == JobStatus.FINISHED)
                    .collect(Collectors.toList());
            
            // Remove all finished Job objects from the jobs LinkedList
            jobs.removeAll(finishedJobs);
        }
        
        return finishedJobs;
    }
    
    public void stopAllJobs() {
        // Iterate through the LinkedList of Job objects
        for (Job job : jobs) {
            // If the current Job's status is RUNNING
            if (job.getStatus() == JobStatus.RUNNING) {
                // Stop the Job (sets the Job's status to INTERRUPTED)
                job.stop();
                
                System.out.printf("JobManager - INFO: Cancelled Job %d\n", job.getIdNumber());
            }
        }
    }
    
}
