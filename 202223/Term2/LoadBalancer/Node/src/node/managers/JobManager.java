package node.managers;

import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;
import node.job.Job;
import node.job.JobStatus;

public class JobManager {
    //
    private static JobManager instance;
    
    //
    private final LinkedList<Job> jobs;
    
    // Mutex used for exclusive access to runningJobs
    private final Object jobsLock = new Object();
    
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
    
    public void startJob(int jobIdNumber, int jobExectutionTime) {
        //
        Job newJob = new Job(jobIdNumber, jobExectutionTime);
        
        synchronized (jobsLock) {
            //
            jobs.add(newJob);
        }
        
        //
        newJob.start();
        System.out.printf("JobManager - INFO: Started Job %d with Execution Time of %d seconds\n", jobIdNumber, jobExectutionTime);
    }
    
    public List<Job> getFinishedJobs() {
        List<Job> finishedJobs = null;
        
        //
        synchronized (jobsLock) {
            //
            finishedJobs = jobs
                    .stream()
                    .filter(job -> job.getStatus() == JobStatus.FINISHED)
                    .collect(Collectors.toList());
            
            //
            jobs.removeAll(finishedJobs);
        }
        
        return finishedJobs;
    }
    
    public void stopAllJobs() {
        //
        for (Job job : jobs) {
            //
            if (job.getStatus() == JobStatus.RUNNING) {
                //
                job.stop();
                
                System.out.printf("JobManager - INFO: Cancelled Job %d\n", job.getIdNumber());
            }
        }
    }
    
}
