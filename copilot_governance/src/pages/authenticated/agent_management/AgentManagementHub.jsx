import Navbar from '../../../components/Navbar';

import AgentCreationForm from './forms/AgentCreationForm';

const AgentManagementHub = () => {
    return(
        <div>
            <Navbar />

            <div className='mt-[20px]'>
                <div className='text-center'>
                    <h1 className='text-[28px]'>Agent Management</h1>
                    <p>Home for managing agents.</p>
                </div>

                <AgentCreationForm />

                <div className='flex justify-center mt-[10px]'>
                    <button className='btn btn-accent text-white' onClick={()=>document.getElementById('agent_creation_form').showModal()}>Create an agent</button>
                </div>

                <div>
                    <h2>Your agents:</h2>
                </div>

                <div>
                    <h2>Agents that you manage:</h2>
                </div>
            </div>
        </div>
    );
}

export default AgentManagementHub;