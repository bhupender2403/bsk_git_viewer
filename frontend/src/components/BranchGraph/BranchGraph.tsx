import "./BranchGraph.css"

type Commit = {
    id:string;
    message:string;
    branch:string;
    parents:string[];
}

const commits:Commit[] = [
    {id:"A",message:"Message for A",branch:"main",parents:[]},
    { id: "B", message: "Add README", branch: "main", parents: ["A"] },
    { id: "C", message: "Start feature", branch: "feature", parents: ["B"] },
    { id: "H", message: "Feature work", branch: "feature2", parents: ["B"] },
    { id: "I", message: "Feature work", branch: "feature2", parents: ["H"] },
    { id: "D", message: "Main work", branch: "main", parents: ["B"] },
    { id: "E", message: "Feature work", branch: "feature", parents: ["C"] },
    { id: "F", message: "Merge feature", branch: "main", parents: ["D", "E"] },
    { id: "J", message: "Merge feature", branch: "main", parents: ["F", "I"] },
]

const branchLanes:Record<string,number> = {
    feature2:80,
    main:170,
    feature:260
}

const branchColors: Record<string, string> = {
  main: "#2563eb",
  feature: "#f97316",
  feature2: "red"
};

const COMMIT_GAP = 180;
const LEFT_PADDING = 80;

export default function BranchGraph(){
    const byId = Object.fromEntries(commits.map((c,index) => [c.id, {...c,index}]));

    const getX = (index:number) => LEFT_PADDING + index * COMMIT_GAP;
    const getY = (branch:string) => branchLanes[branch]

    const width = 2*LEFT_PADDING+commits.length*COMMIT_GAP
    const height = 300;


    return (
        <div className="timeline-scroll">
            <div className="timeline-canvas" style={{width}}>
                <svg width={width} height={height} className="timeline-svg">
                    {
                        commits.flatMap((commit,index) =>
                            commit.parents.map((parentId) =>{
                                const parent = byId[parentId]

                                const x1 = getX(parent.index)
                                const y1 = getY(parent.branch)
                                const x2 = getX(index)
                                const y2 = getY(commit.branch)

                                return (
                                    
                                    <path
                                        key={`${parentId}-${commit.id}`}
                                        d={`M ${x1} ${y1} C ${(x1 + x2) / 2} ${y1}, ${(x1 + x2) / 2} ${y2}, ${x2} ${y2}`}
                                        fill="none"
                                        stroke={branchColors[commit.branch]}
                                        strokeWidth="4"
                                        />
                                    
                                );
                            })
                        )
                    }

                    {
                        commits.map((commit,index)=>{
                            const x = getX(index)
                            const y = getY(commit.branch)
                            return (
                                <g key = {commit.id}>
                                    <circle 
                                    cx = {x}
                                    cy = {y}
                                    r = "11"
                                    fill = {branchColors[commit.branch]}
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
