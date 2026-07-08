import type { ResponseData } from "../../types/git";
import CommitMarker from "./CommitMarker";
import "./RepoTimeLine.css"
import TimeLineTicks from "./TimeLineTicks";



interface RepoTimeLineProps{
    repo:ResponseData;
}

export default function RepoTimeLine({repo}:RepoTimeLineProps){

    if (repo === null){
        return (
            <div className="repo-page">
                <h1>Loading repository</h1>
            </div>
        )
    }

    const commits = [...repo.data.commits.sort(
        (a,b) => a.commit_time-b.commit_time
    )]

    if (commits.length === 0){
        return (
            <div className="repo-page">
                <h1>{repo.data.name}</h1>
                <p>No commits found</p>
            </div>
        )
    }

    const minTime = commits[0].commit_time
    const maxTime = commits[commits.length-1].commit_time
    const range = Math.max(maxTime-minTime,1)

    const getLeft = (time:number):string =>
        `${((time - minTime) / range) * 100}%`;



    const ticks = Array.from({ length: 5 }, (_, i) => {
        const time = minTime + (range * i)/4;
        return {
            left: `${( i / 4 ) * 100}%`,
            time,
        };
    });


    return (
    <div className="repo-page">
        <div className="top-header" style={{width:"100%"}}>
            <div className="repo-label" >{repo.data.name}</div>
        </div>
        
        <div className="timeline-wrapper">
            <div className="timeline-line"/>
                <TimeLineTicks ticks={ticks} />

                {commits.map((commit) => (
                    <CommitMarker
                        key={commit.commit_id}
                        commit={commit}
                        left={getLeft(commit.commit_time)}
                    />
                ))}
                
            </div>
    </div>)
    



}