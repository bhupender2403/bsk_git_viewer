import { formatCommitTime } from "../../utils/time"

interface Tick{
    left:string
    time:number
}

interface Props{
    ticks:Tick[]
}

export default function TimeLineTicks({ticks}:Props){
    return (
        <>
        {ticks.map((tick, index) => (
            <div key={index} className="timeline-tick" style={{ left: tick.left }}>
            <div className="tick-line" />
            <div className="tick-label">{formatCommitTime(tick.time)}</div>
            </div>
        ))}
        </>
    );
}