import { useEffect,useState} from "react";

function App(){

  const [data, setData] = useState<any>(null);

  useEffect(() =>{
    fetch("http://127.0.0.1:8000/api/repository?path=.")
    .then((res)=> res.json()).then(setData)
  },[])

  return (
    <main>
      <h1>BSK Git Viewer</h1>
      <pre>{JSON.stringify(data,null,2)}</pre>
    </main>
  )

}

export default App