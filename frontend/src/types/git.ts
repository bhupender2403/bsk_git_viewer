export interface Commit{
    commit_id:string;
    author:string;
    message:string;
    commit_time:number;
    parents:string[];
}

export interface RepoData{
    name:string,
    commits:Commit[],
    brances:Record<string,string>
}

export interface ResponseData{
    status:string;
    path:string;
    git_path:string;
    message:string;
    data:RepoData;
}