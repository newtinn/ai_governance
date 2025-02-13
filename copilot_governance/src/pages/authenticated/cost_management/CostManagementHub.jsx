import Navbar from '../../../components/Navbar';

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
    { name: 'Jan', cost: 10 },
    { name: 'Feb', cost: 5 },
    { name: 'Mar', cost: 6.5 },
    { name: 'Apr', cost: 2 },
    { name: 'May', cost: 10 },
    { name: 'June', cost: 8 },
    { name: 'July', cost: 11 },
    { name: 'Aug', cost: 10.1 },
    { name: 'Sep', cost: 2 },
    { name: 'Oct', cost: 5.5 },
    { name: 'Nov', cost: 9.14 },
    { name: 'Dec', cost: 4.03 },
];

const apiURL = import.meta.env.VITE_APP_API_URL;

const CostManagementHub = () => {

    const navigate = useNavigate();

    const [usageData, setUsageData] = useState(data);
    const [agentsList, setAgentsList] = useState([]);

    const getAgents = () => {
        fetch(`${apiURL}/get_agents`, { method: 'GET' })
        .then((res)=>{
            if (res.status !== 404) {
                return res.json();
            }
        })
        .then((data)=> {
            setAgentsList(data);
        });
    }

    useEffect(()=> {
        getAgents();
    }, []);

    return(
        <div className='mb-[100px]'>
            <Navbar />
            <div className='mt-[20px] text-center'>
                <h1 className='text-[28px]'>Cost Management</h1>
                <p>This is Cost Management for Microsoft Copilot.</p>

                <div>
                    The cost of one prompt of conversation in Microsoft Copilot is £0.01 
                </div>

                {/* Recharts for graphing */}
                <div className="flex justify-center flex-col items-center">
                    <h2 className="text-lg font-semibold mt-6">Total cost of all agents (£)</h2>
                    <ResponsiveContainer width="50%" height={400}>
                        <LineChart data={usageData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="cost" stroke="#8884d8" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Table of agents */}
                <div className='max-w-[700px] ml-auto mr-auto mt-[20px]'>
                    { agentsList.length > 0 ?
                        <div className="overflow-x-auto">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Agent Name</th>
                                        <th>Description</th>
                                        <th>Owner</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {agentsList.map((agent, key)=> (
                                        <tr onClick={()=>navigate(`/cost-management/agent/${agent.id}`)} className='cursor-pointer' key={key*1000}>
                                            <th>{agent.id}</th>
                                            <td>{agent.name}</td>
                                            <td className='max-w-[200px]'>{agent.description}</td>
                                            <td>{agent.owner}</td>
                                            <td>{agent.status}</td>
                                        </tr>
                                    ))
                                    }
                                </tbody>
                            </table>
                        </div>
                        :
                        <div>
                            <p>No data to show - you have not created any agents.</p>
                        </div>
                    }
                </div>
            </div>
        </div>
    );
}

export default CostManagementHub;