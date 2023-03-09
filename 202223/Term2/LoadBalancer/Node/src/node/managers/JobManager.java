package node.managers;

import java.util.LinkedList;
import java.util.stream.Collectors;
import node.job.Job;
import node.job.JobStatus;

public class JobManager {
    private static JobManager instance = null; 
    
    private LinkedList<Job> jobs = null;
    
    private final Object jobsMutex = new Object();
    
    private JobManager() {
        this.jobs = new LinkedList<>();
    }
    
    public static JobManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new JobManager();
        return instance;
    }
    
    public void startJob(int idNumber, int executionTime) {
        Job job = new Job(idNumber, executionTime);
        
        synchronized (jobsMutex) {
            jobs.add(job);
        }
        
        job.start();
        System.out.printf("JobManager - INFO: Started Job %d with a %d second Execution Time\n", job.getIdNumber(), job.getExecutionTime());
    }
    
    public LinkedList<Job> getAllFinishedJobs() {
        LinkedList<Job> finishedJobs = null;
        
        synchronized(jobsMutex) {
            finishedJobs = jobs.stream()
                    .filter(job -> job.getStatus() == JobStatus.FINISHED)
                    .collect(Collectors.toCollection(LinkedList::new));
            
            jobs.removeAll(finishedJobs);
        }
        
        return finishedJobs;
    }
    
    public void stopAllRunningJobs() {
        synchronized(jobsMutex) {
            for (Job job: jobs) {
                if (job.getStatus() == JobStatus.RUNNING) {
                    job.stop();
                    System.out.printf("JobManager - INFO: Stopped Job %d\n", 0);
                }
            }
        }
    }
    
    
}
