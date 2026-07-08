import type {Commit} from "../../types/git"
import { formatCommitTime } from "../../utils/time"


interface Props {
    commit:Commit
    left:string
}

export default function CommitMarker({commit,left}:Props){
    return (
        <div key={commit.commit_id} className="commit-point" style ={{left:left}}>
            <div className="commit-circle">
            </div>
            <div className="commit-card">
                <strong>{commit.message.split("\n")[0]}</strong>

                <p>{formatCommitTime(commit.commit_time)}</p>

                <p>{commit.author}</p>

                <code>{commit.commit_id.substring(0, 7)}</code>
                </div>
        </div>
)
}