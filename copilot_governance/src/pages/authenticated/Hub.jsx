import Navbar from "../../components/Navbar";

const Hub = () => {
    return(
        <div>
            <Navbar />
            <h1 className='text-center mt-[20px] text-3xl'>User Hub</h1>
            <div className='flex justify-center flex-col max-w-[250px] ml-auto mr-auto mt-[10px]'>
                <a href='/hub/cost-management' className='btn btn-primary'>Cost Management</a>
                <button className='btn btn-neutral mt-[10px]' onClick={()=>alert('Going to data governance')}>Data Governance</button>
                <a href='/hub/agent-management' className='btn btn-secondary mt-[10px]'>Agent Management</a>
            </div>
        </div>
    );
}

export default Hub;