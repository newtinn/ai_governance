import { useState, useEffect } from 'react';
import { data, useParams } from 'react-router-dom';

import Navbar from "../../../components/Navbar"

import { Tooltip, Legend, PieChart, Pie, Cell } from "recharts";

const data_piechart = [
    { name: "Available", value: 80 },
    { name: "Used", value: 30 },
  ];
  
const COLORS = ["#00C49F", "#ED6A5E"];

const apiURL = import.meta.env.VITE_APP_API_URL;

const CostManagementAgent = () => {

    const { id } = useParams();

    const [agent, setAgent] = useState([]);
    const [pieData, setPieData] = useState(data_piechart);

    const getAgent = () => {
        fetch(`${apiURL}/get_agent/${id}`, { method: 'GET' })
        .then((res)=>{
            if (res.status === 200) return res.json();
        })
        .then((data)=> {
            setAgent(data);

            // setting the pie chart
            let currentPieData = pieData;
            currentPieData[0].value = data.budget-data.current_spend.amount;
            currentPieData[1].value = data.current_spend.amount;
            setPieData(currentPieData);
        });
    }

    useEffect(()=> {
        getAgent();
    }, []);

    return(
        <div>
            <Navbar />
            <div className='mt-[20px] text-center'>
                {   agent["agent"] !== undefined &&
                    <div>
                        <h1 className='text-[28px]'>{agent.agent.display_name !== null && <span>{agent.agent.display_name}</span>}</h1>
                        <p>Description of the agent</p>

                        <div className='mt-[50px] text-center'>
                            <h2 className="text-lg font-semibold">Amount used for this month (£)</h2>
                            <div className='flex justify-center'>
                                <PieChart width={400} height={400}>
                                    <Pie
                                    data={data_piechart}
                                    cx="50%"
                                    cy="50%"
                                    label
                                    outerRadius={120}
                                    fill="#8884d8"
                                    dataKey="value"
                                    >
                                    {data_piechart.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                    </Pie>
                                    <Tooltip />
                                    <Legend />
                                </PieChart>
                            </div>
                            <div className='mt-[10px]'>
                                <h2>Status: {agent.agent.active ? 'Active' : 'Disabled'}</h2>
                                <h2>Files used: ...</h2>
                            </div>
                        </div>
                    </div>
                }
            </div>
        </div>
    );
}

export default CostManagementAgent;