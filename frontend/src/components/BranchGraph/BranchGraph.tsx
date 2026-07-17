import { getColor } from "../../utils/color";
import "./BranchGraph.css"

type Commit = {
    id:string;
    message:string;
    branch:string;
    line:number;
    parents:string[];
    commitTime:number;
}


type RepoGraph = {
    branch_list:string[];
    commits:Commit[];
}


const commits: Commit[] = [
  { id: "A", message: "Message for A", branch: "main",     line: 0, parents: [],         commitTime: 1710000012 },
  { id: "A1", message: "Add README",    branch: "main",     line: 1, parents: ["A"],      commitTime: 1710000079 },
  { id: "B", message: "Add README",    branch: "main",     line: 0, parents: ["A"],      commitTime: 1710000079 },
  { id: "C", message: "Start feature", branch: "feature",  line: 0, parents: ["B"],      commitTime: 1710000158 },
  { id: "H", message: "Start feature", branch: "feature2", line: 0, parents: ["B"],      commitTime: 1710000187 },
  { id: "I", message: "Feature work",  branch: "feature2", line: 0, parents: ["H"],      commitTime: 1710000274 },
  { id: "D", message: "Main work",     branch: "main",     line: 0, parents: ["B"],      commitTime: 1710000311 },
  { id: "E", message: "Feature work",  branch: "feature",  line: 0, parents: ["C"],      commitTime: 1710000398 },
  { id: "F", message: "Merge feature", branch: "main",     line: 0, parents: ["D", "E"], commitTime: 1710000465 },
  { id: "J", message: "Merge feature", branch: "main",     line: 0, parents: ["F", "I"], commitTime: 1710000532 },
  { id: "E1", message: "Feature work",  branch: "feature",  line: 1, parents: ["E"],      commitTime: 1710000898 },
];


const repoGraph:RepoGraph = {
    branch_list: ["main", "feature","feature2"],
    commits:commits
}

// const branchLanes:Record<string,number> = {
//     feature2:80,
//     main:170,
//     feature:260
// }

// const branchColors: Record<string, string> = {
//   main: "#2563eb",
//   feature: "#f97316",
//   feature2: "red"
// };




const COMMIT_GAP = 180;
const LEFT_PADDING = 80;


function getBranchYLocationMap(
    branchNames:string[],
    maxLineNumMap:Map<string,number>,
    INITIAL_PADDING:number,
    BEFORE_BRANCH_GAP:number,
    BEFORE_LINE_GAP:number
): Map<string,number> {
    const locationMap:Map<string,number> = new Map<string,number>();

    let y = INITIAL_PADDING;
    
    for(const branch of branchNames){
        locationMap.set(
            branch,
            y
        )
        const maxLine = maxLineNumMap.get(branch)??0
        y += maxLine*BEFORE_LINE_GAP;
        y += BEFORE_BRANCH_GAP;
    }

    return locationMap
}

function getPath(x1:number,y1:number,x2:number,y2:number):string{
    if(y1<=y2){
        return `M ${x1} ${y1} C ${x1} ${y2}, ${x1} ${y2}, ${x2} ${y2}`
    }else{
        return `M ${x1} ${y1} C ${x2} ${y1}, ${x2} ${y1}, ${x2} ${y2}`
    }
}


export default function BranchGraph(){
    const byId = Object.fromEntries(commits.map((c,index) => [c.id, {...c,index}]));

    const maxLineNum:Map<string,number> = new Map<string,number>();

    for (const {branch,line} of commits){
        maxLineNum.set(
            branch,
            Math.max(maxLineNum.get(branch) ?? -Infinity, line)   
        );
    }

    const BEFORE_LINE_PADDING:number = 50;
    const INITIAL_PADDING:number = 100;
    const BEFORE_BRANCH_PADDING:number = 100;
    const branchY:Map<string,number>  = getBranchYLocationMap(repoGraph.branch_list,maxLineNum, INITIAL_PADDING, BEFORE_BRANCH_PADDING, BEFORE_LINE_PADDING)

    console.log(maxLineNum)
    console.log(branchY)
    // const maxTime = commits.reduce(
    //     (max, c) => Math.max(max, c.commitTime), -Infinity
    // )
    // const minTime = commits.reduce(
    //     (minV,c) => Math.min(minV,c.commitTime), Infinity
    // )

    // const range = maxTime-minTime

    // const initialTimePadding:number = 1000;

    const branchColors:Map<string, string> = new Map<string,string>()

    repoGraph.branch_list.forEach((branch,index)=>(
        branchColors.set(
            branch,
            getColor(index)
        )
    ))

    const getX = (index:number) => LEFT_PADDING + index * COMMIT_GAP;
    const getY = (branch:string, line:number):number => (branchY.get(branch) ?? 0)+line*BEFORE_LINE_PADDING;


    const totalMainLines:number = [...maxLineNum.values()].reduce((total,value)=> total+value, 0)

    const width = 2*LEFT_PADDING+commits.length*COMMIT_GAP
    const height = INITIAL_PADDING+repoGraph.branch_list.length*BEFORE_BRANCH_PADDING+totalMainLines*BEFORE_LINE_PADDING;


    return (
        <div className="timeline-scroll">
            <div className="timeline-canvas" style={{width}}>
                <svg width={width} height={height} className="timeline-svg">
                    {
                        commits.flatMap((commit,index) =>
                            commit.parents.map((parentId) =>{
                                const parent = byId[parentId]

                                const x1 = getX(parent.index)
                                const y1 = getY(parent.branch, parent.line)
                                const x2 = getX(index)
                                const y2 = getY(commit.branch, commit.line)

                                return (
                                    
                                    <path
                                        key={`${parentId}-${commit.id}`}
                                        d={getPath(x1,y1,x2,y2)}
                                        fill="none"
                                        stroke={branchColors.get(commit.branch)}
                                        strokeWidth="4"
                                        />
                                    
                                );
                            })
                        )
                    }

                    {
                        commits.map((commit,index)=>{
                            const x = getX(index)
                            const y = getY(commit.branch, commit.line)
                            return (
                                <g key = {commit.id}>
                                    <circle 
                                    cx = {x}
                                    cy = {y}
                                    r = "11"
                                    fill = {branchColors.get(commit.branch)}
                                    />
                                    <text x ={x-12} y = {y-12} className="commit-id">
                                        {commit.id}
                                    </text>
                                </g>
                            )
                        })

                    }
                </svg>

            </div>


        </div>
    )

}
