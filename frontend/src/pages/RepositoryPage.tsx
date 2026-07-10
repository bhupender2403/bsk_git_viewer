import BranchGraph from "../components/BranchGraph/BranchGraph";
import RepoTimeLine from "../components/RepoTimeLine";
import type { ResponseData } from "../types/git";

interface Props {
  repo: ResponseData;
}

export default function RepositoryPage({ repo }: Props) {
  return <div>
          <RepoTimeLine repo={repo} />
          <BranchGraph/>
        </div>
}