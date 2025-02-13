import Navbar from "../components/Navbar";

const Home = () => {
    return(
        <div>
            <Navbar />
            <h1 className='text-center mt-[20px] text-3xl'>Home</h1>
            <div className='flex justify-center mt-[10px]'>
                <button className='btn btn-primary' onClick={()=>alert('Hello World!')}>Click me!</button>
            </div>
        </div>
    );
}

export default Home;