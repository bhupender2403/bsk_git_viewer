import RepoTimeLine from "../components/RepoTimeLine";
import type { ResponseData } from "../types/git";

interface Props {
  repo: ResponseData;
}

export default function RepositoryPage({ repo }: Props) {
  return <RepoTimeLine repo={repo} />;
}