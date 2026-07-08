

export function formatCommitTime(unixTime:number):string{
    return new Date(unixTime*1000).toLocaleString("en-In",{
            day:"2-digit",
            month:"short",
            year:"numeric",
            hour:"2-digit",
            minute:"2-digit",
        })
}