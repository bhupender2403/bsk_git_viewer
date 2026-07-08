import type { ResponseData } from "../../types/git";
import "./RepoTimeLine.css"



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

    const formatDate = (unixTime:number) =>
        new Date(unixTime*1000).toLocaleString("en-In",{
            day:"2-digit",
            month:"short",
            year:"numeric",
            hour:"2-digit",
            minute:"2-digit",
        })

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
                {ticks.map((tick, index) => (
                <div
                    key={index}
                    className="timeline-tick"
                    style={{ left: tick.left }}
                >
                    <div className="tick-line" />
                    <div className="tick-label">{formatDate(tick.time)}</div>
                </div>
                ))}

                {commits.map((commit) =>(
                    <div key={commit.commit_id} className="commit-point" style ={{left:getLeft(commit.commit_time)}}>
                        <div className="commit-circle">
                        </div>
                        <div className="commit-card">
                            <strong>{commit.message.split("\n")[0]}</strong>

                            <p>{formatDate(commit.commit_time)}</p>

                            <p>{commit.author}</p>

                            <code>{commit.commit_id.substring(0, 7)}</code>
                            </div>
                    </div>
                ))
                }
            </div>
    </div>)
    



}