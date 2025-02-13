import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import Navbar from '../../../components/Navbar';

import AgentAddKnowledgeSourceForm from './forms/AgentAddKnowledgeSourceForm';
import AgentChat from '../../../components/Agent/AgentChat';

const apiURL = import.meta.env.VITE_APP_API_URL;

const AgentManagementAgent = () => {

    const { id } = useParams();

    const [agent, setAgent] = useState([]);

    const getAgent = () => {
        fetch(`${apiURL}/get_agent/${id}`, { method: 'GET' })
        .then((res)=>{
            if (res.status === 200) return res.json();
        })
        .then((data)=> {
            setAgent(data);
        });
    }

    useEffect(()=> {
        //getAgent();
    }, []);

    return(
        <div>
            <Navbar />

            <div className='mt-[20px]'>
                <div className='text-center'>
                    { agent.agent !== undefined &&
                    <div>
                        <h1 className='text-[28px]'>{agent.agent.display_name}</h1>
                        <p>Status: {agent.agent.status}</p>
                        <p>Hosted Location: {agent.agent.location}</p>
                        <p>Owner: {agent.agent.owner}</p>
                    </div>
                    }
                    {
                        agent.agent === undefined &&
                        <div>
                            <h1 className='text-[28px]'>Agent</h1>
                            <p>Status: Waiting for approval</p>
                            <p>Hosted Location: UK South</p>
                            <p>Owner: John Doe</p>
                        </div>
                    }
                </div>
                <div className='text-center mt-[50px]'>
                    <h2 className='font-bold mb-[10px]'>Knowledge sources</h2>
                    
                    <AgentAddKnowledgeSourceForm id={id} />
                    <button className='btn btn-neutral mb-[10px]' onClick={()=>document.getElementById('agent_add_knowledge_source_form').showModal()}>Add Knowledge Source</button>

                    <p className='mt-[10px]'>Current knowledge sources:</p>
                    <div className='max-w-[700px] flex justify-center ml-auto mr-auto'>
                        <div className="overflow-x-auto">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Knowledge Source Name</th>
                                        <th>Source</th>
                                        <th>Approval Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <th>FAQ</th>
                                        <td className='max-w-[200px]'>https://website.com/</td>
                                        <td>Waiting for approval</td>
                                    </tr>
                                    <tr>
                                        <th>Credit Card</th>
                                        <td className='max-w-[200px]'>https://website.com/</td>
                                        <td className='bg-[red] text-white'>Rejected</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div className='flex justify-center w-[900px] ml-auto mr-auto mt-[20px]'>
                    <AgentChat />
                </div>
            </div>
        </div>
    );
}

export default AgentManagementAgent;