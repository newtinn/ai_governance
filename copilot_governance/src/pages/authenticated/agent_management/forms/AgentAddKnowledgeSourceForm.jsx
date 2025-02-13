import { useState, useRef } from 'react';

const AgentAddKnowledgeSourceForm = (id) => {

    const [name, setName] = useState('');
    const [source, setSource] = useState('');
    const [approved, setApproved] = useState(false);

    const modalRef = useRef(null);

    const handleSubmit = () => {
        // add file to knowledge bank using blob storage

        // resetting values for form
        setName('');
        setSource('');

        document.getElementById('name').value = '';
        document.getElementById('source').value = '';

        modalRef.current.close();
    }

    return(
        <div>
            <dialog id="agent_add_knowledge_source_form" className="modal" ref={modalRef}>
                <div className="modal-box">
                    <form method="dialog">
                    {/* if there is a button in form, it will close the modal */}
                    <button className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
                    </form>
                    <h3 className="font-bold text-lg">Add a knowledge source</h3>
                    <div className="py-4">
                        <div className='flex flex-col text-left'>
                            <div className='flex flex-col'>
                                <label>Name:</label>
                                <input onChange={(e)=>setName(e.target.value)} type="text" id="name" className='input input-bordered w-full mt-[5px]' placeholder="Enter knowledge source name" />
                            </div>

                            <div className='flex flex-col mt-[15px]'>
                                <label>Source:</label>
                                <input onChange={(e)=>setSource(e.target.files[0])} type="file" id="source" className='file-input file-input-bordered w-full' placeholder="Enter source URL or details" />
                            </div>

                            <button onClick={()=>handleSubmit()} className='btn btn-neutral mt-[20px]'>Submit</button>
                        </div>
                    </div>
                </div>
            </dialog>
        </div>
    );
}

export default AgentAddKnowledgeSourceForm;