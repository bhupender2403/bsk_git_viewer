import { useEffect,useState} from "react";
import RepoTimeLine from "./components/RepoTimeLine/RepoTimeLine";

function App(){

  const [data, setData] = useState<any>(null);

  useEffect(() =>{
    fetch("http://127.0.0.1:8000/api/repository?path=.")
    .then((res)=> res.json()).then(setData)
  },[])

  return <RepoTimeLine repo={data} />;

}

export default App