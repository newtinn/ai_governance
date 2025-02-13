import { useEffect, useState } from 'react';

import Navbar from '../../../../components/Navbar';

const apiURL = import.meta.env.VITE_APP_API_URL;

const AgentCreationForm = () => {

    const [agentName, setAgentName] = useState('');
    const [agentDescription, setAgentDescription] = useState('');
    const [agentModel, setAgentModel] = useState('');
    const [agentLocation, setAgentLocation] = useState('uksouth');
    const [agentOwner, setAgentOwner] = useState('');
    const [agentEmail, setAgentEmail] = useState('');
    const [agentBudget, setAgentBudget] = useState(1);

    const createAgent = () => {
        fetch(`${apiURL}/`, { method: 'GET' })
        .then((res)=>res.json())
        .then((data)=> {
            console.log(data);
        });
    }

    return(
        <div>
            <dialog id="agent_creation_form" className="modal">
            <div className="modal-box">
                <form method="dialog">
                {/* if there is a button in form, it will close the modal */}
                <button className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
                </form>
                <h3 className="font-bold text-lg">Agent Creation Form</h3>
                <div className="py-4">
                    <div>
                        <div className='flex flex-col'>
                            <label className='mb-[5px]'>Name of your agent:</label>
                            <input type='text' className='input input-bordered w-full max-w-xs' required onChange={(e)=>setAgentName(e.target.value)} />
                        </div>

                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Description of your agent:</label>
                            <input type='text' className='input input-bordered w-full max-w-xs' required maxLength={255} onChange={(e)=>setAgentDescription(e.target.value)} />
                        </div>

                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Model of agent to use:</label>
                            <select className="select select-bordered w-full max-w-xs" onChange={(e)=>setAgentModel(e.target.value)}>
                                <option>GPT 3.5</option>
                                <option>GPT 4</option>
                            </select>
                        </div>
                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Location of agent:</label>
                            <select className="select select-bordered w-full max-w-xs" onChange={(e)=>setAgentLocation(e.target.value)}>
                                <option value="uksouth">UK South</option>
                                <option value="westeurope">West Europe</option>
                            </select>
                        </div>

                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Owner of agent:</label>
                            <input type='text' className='input input-bordered w-full max-w-xs' required maxLength={255} onChange={(e)=>setAgentOwner(e.target.value)}/>
                        </div>

                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Owner's email:</label>
                            <input type='email' className='input input-bordered w-full max-w-xs' required maxLength={255} onChange={(e)=>setAgentEmail(e.target.value)} />
                        </div>

                        <div className='flex flex-col mt-[10px]'>
                            <label className='mb-[5px]'>Budget (per month) of your agent:</label>
                            <input type='number' className='input input-bordered w-full max-w-xs' required min={1} step={0.01} onChange={(e)=>setAgentBudget(e.target.value)} />
                        </div>

                        <input onClick={()=>createAgent()} type='submit' value='Create' className='btn btn-secondary text-white mt-[20px]'/>
                    </div>
                </div>
            </div>
            </dialog>
        </div>
    );
}

export default AgentCreationForm;